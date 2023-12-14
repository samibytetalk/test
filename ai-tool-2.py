import requests
import json
from azure.storage.blob import BlobServiceClient
from transformers import pipeline

# Azure Cognitive Search service and index details
search_service_name = 'your-search-service-name'
index_name = 'your-index-name'
api_version = '2020-06-30'
api_key = 'your-search-service-api-key'

# Azure Storage Account details
storage_account_name = 'your-storage-account-name'
storage_account_key = 'your-storage-account-key'
container_name = 'your-container-name'

def download_document(blob_service_client, container_name, blob_name):
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)
    document_content = blob_client.download_blob().readall()
    return document_content

def search_documents(query, blob_service_client):
    # Build the search query
    search_url = f'https://{search_service_name}.search.windows.net/indexes/{index_name}/docs/search?api-version={api_version}'
    headers = {
        'Content-Type': 'application/json',
        'api-key': api_key
    }
    payload = {
        'search': query,
        'queryType': 'full',
        'searchMode': 'all'
    }

    # Make the search request
    response = requests.post(search_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        # Parse and return the relevant information
        result = response.json()
        documents = result.get('value', [])
        
        # Fetch the full content of each document from the storage account
        for doc in documents:
            blob_name = doc.get('blob_name')  # Replace with the actual field name storing blob names
            document_content = download_document(blob_service_client, container_name, blob_name)
            doc['content'] = document_content.decode('utf-8')

        return documents
    else:
        print(f"Search request failed with status code: {response.status_code}")
        return []

def find_answer_using_bert(question, document):
    nlp = pipeline("question-answering")
    result = nlp(question=question, context=document)
    return result['answer']

def main():
    # Initialize Azure Storage Blob client
    blob_service_client = BlobServiceClient(account_url=f'https://{storage_account_name}.blob.core.windows.net', credential=storage_account_key)

    while True:
        question = input("Ask a question (type 'exit' to quit): ")
        
        if question.lower() == 'exit':
            break

        # Process the question
        processed_question = question.lower()  # Placeholder, replace with actual processing

        # Search for documents
        search_results = search_documents(processed_question, blob_service_client)

        # Find answer using BERT-based question-answering
        for result in search_results:
            document_content = result['content']
            answer = find_answer_using_bert(processed_question, document_content)
            
            print(f"\nDocument ID: {result['id']}")
            print(f"Answer: {answer}\n")

if __name__ == "__main__":
    main()
