import requests
import json
from azure.storage.blob import BlobServiceClient
from docx import Document
import io

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

def extract_text_from_docx(docx_content):
    doc = Document(io.BytesIO(docx_content))
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    return '\n'.join(full_text)

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
            docx_text = extract_text_from_docx(document_content)
            doc['content'] = docx_text

        return documents
    else:
        print(f"Search request failed with status code: {response.status_code}")
        return []

def process_question(question):
    # Tokenize the question using spaCy
    doc = nlp(question)
    
    # Extract lemmatized tokens
    processed_question = ' '.join([token.lemma_ for token in doc])

    return processed_question

def find_answer_in_documents(question, documents):
    # Simple keyword matching to find the answer in document content
    question_keywords = set(processed_question.split())
    answers = []

    for doc in documents:
        document_keywords = set(doc['content'].lower().split())
        common_keywords = question_keywords.intersection(document_keywords)
        
        if common_keywords:
            # Find the relevant section based on some criteria (e.g., paragraphs containing keywords)
            relevant_section = find_relevant_section(doc['content'], common_keywords)
            answers.append(relevant_section)

    return answers

def find_relevant_section(full_text, keywords):
    # Find paragraphs containing keywords as a relevant section
    paragraphs = full_text.split('\n\n')  # Assuming paragraphs are separated by double line breaks
    
    for paragraph in paragraphs:
        if any(keyword in paragraph.lower() for keyword in keywords):
            return paragraph

    return 'No relevant section found'

def main():
    # Initialize Azure Storage Blob client
    blob_service_client = BlobServiceClient(account_url=f'https://{storage_account_name}.blob.core.windows.net', credential=storage_account_key)

    while True:
        question = input("Ask a question (type 'exit' to quit): ")
        
        if question.lower() == 'exit':
            break

        processed_question = process_question(question)
        search_results = search_documents(processed_question, blob_service_client)
        answers = find_answer_in_documents(processed_question, search_results)

        print(f"\nAnswers: {', '.join(answers)}\n")

if __name__ == "__main__":
    main()
