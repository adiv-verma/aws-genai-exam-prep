Now, you will have an opportunity to build a proof-of-concept document processing solution that extracts information from insurance claim documents and generates summaries using Amazon Bedrock.

Bonus assignments are an open-ended way for you to assess your overall knowledge of this task. You can share your answers on social media and tag #awsexamprep for us to review.
Bonus assignment
Scenario
An insurance company wants to automate processing of claim documents to reduce manual effort and improve consistency.
Step 1. Design the architecture (Skill 1.1.1)
Create a simple architecture diagram showing the following:
Document storage (Amazon S3)
Processing workflow
Foundation model integration
Response generation
Select appropriate Amazon Bedrock models for the following:
Document understanding
Information extraction
Summary generation
Step 2. Implement proof-of-Concept (Skill 1.1.2)
Set up AWS environment:
aws s3 mb s3://claim-documents-poc-<your-initials>
Create a Python application with the following:
Document upload functionality
Amazon Bedrock integration
Simple RAG component using policy information
Claim summary generation
Step 3. Create reusable components (Skill 1.1.3)
Develop standardized for the following:

Prompt template manager
Model invoker
Basic content validator
Step 4. Test and evaluate
Test with 2-3 sample documents
Compare performance of different models
Document findings and recommendations

TESTING

EVALUATION
Create sample claim documents (or use public datasets)
Upload to your S3 bucket
Run the processor on different document types
Compare results from different models
Document your findings
Core implementation examples
Basic document processor


import boto3
import json

# Initialize clients
s3 = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime')

def process_document(bucket, key, model_id='anthropic.claude-v2'):
    # Get document from S3
    response = s3.get_object(Bucket=bucket, Key=key)
    document_text = response['Body'].read().decode('utf-8')
    
    # Create prompt for information extraction
    prompt = f"""
    Extract the following information from this insurance claim document:
    - Claimant Name
    - Policy Number
    - Incident Date
    - Claim Amount
    - Incident Description
    
    Document:
    {document_text}
    
    Return the information in JSON format.
    """
    
    # Invoke Bedrock model
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps({
            "prompt": prompt,
            "temperature": 0.0,
            "max_tokens_to_sample": 1000
        })
    )
    
    # Parse response
    response_body = json.loads(response['body'].read())
    extracted_info = response_body['completion']
    
    # Generate summary
    summary_prompt = f"""
    Based on this extracted information:
    {extracted_info}
    
    Generate a concise summary of the claim.
    """
    
    summary_response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=json.dumps({
            "prompt": summary_prompt,
            "temperature": 0.7,
            "max_tokens_to_sample": 500
        })
    )
    
    summary_body = json.loads(summary_response['body'].read())
    summary = summary_body['completion']
    
    return {
        "extracted_info": extracted_info,
        "summary": summary
    }

# Example usage
if __name__ == "__main__":
    result = process_document('claim-documents-poc-xyz', 'claims/claim1.txt')
    print(json.dumps(result, indent=2))
Simple prompt template manager


class PromptTemplateManager:
    def __init__(self):
        self.templates = {
            "extract_info": """
            Extract the following information from this insurance claim document:
            - Claimant Name
            - Policy Number
            - Incident Date
            - Claim Amount
            - Incident Description
            
            Document:
            {document_text}
            
            Return the information in JSON format.
            """,
            
            "generate_summary": """
            Based on this extracted information:
            {extracted_info}
            
            Generate a concise summary of the claim.
            """
        }
    
    def get_prompt(self, template_name, **kwargs):
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template {template_name} not found")
        
        return template.format(**kwargs)
Basic model comparison


def compare_models(document_text, models=['anthropic.claude-v2', 'anthropic.claude-instant-v1']):
    results = {}
    
    for model in models:
        start_time = time.time()
        
        # Process with current model
        response = bedrock_runtime.invoke_model(
            modelId=model,
            body=json.dumps({
                "prompt": "Extract key information from this document: " + document_text,
                "temperature": 0.0,
                "max_tokens_to_sample": 1000
            })
        )
        
        # Calculate metrics
        elapsed_time = time.time() - start_time
        response_body = json.loads(response['body'].read())
        output = response_body['completion']
        
        results[model] = {
            "time_seconds": elapsed_time,
            "output_length": len(output),
            "output_sample": output[:100] + "..."
        }
    
    return results
Extra challenging steps
To #neverstoplearning and once you've completed this bonus assignment, consider these extensions to further enhance your skills.

Add a simple web interface using Flask
Implement a knowledge base with policy information
Add content filtering for sensitive information
Create a simple feedback mechanism