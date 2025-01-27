import streamlit as st
import os
import json
from typing import List, Optional, Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate

from ppt import generate_ppt
from prompts import relevant_page_prompt, slides_prompt,web_prompt

load_dotenv()

class PDFSlideGenerator:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model)
        
    def load_pdf(self, uploaded_file):
        """Load PDF from Streamlit uploaded file"""
        try:
            # Temporarily save file
            with open(uploaded_file.name, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            loader = PyPDFLoader(uploaded_file.name)
            documents = loader.load()
            
            # Remove temporary file
            os.remove(uploaded_file.name)
            
            return documents
        except Exception as e:
            st.error(f"Error loading PDF: {e}")
            return []
        
    def generate_relevant_pages(self,question,pdf_documents):
        """Generate relevant pages containing the answer of the prompt from the pdf"""
        context=[]
        generate_pages=ChatPromptTemplate(
                    messages=[
                        SystemMessagePromptTemplate.from_template(relevant_page_prompt),
                    ],
                    input_variables=["question", "text"],
                ) | self.llm
        for page in pdf_documents:
            context.append(generate_pages.invoke({"question":question,"text":page.page_content,"page":page.metadata["page_label"]}).content)
        return context

    def filter_list(self,context):
        """Filter the text to create valid list without empty strings"""
        return [x for x in context if x]

    def get_content_by_page_label(self,documents, target_page_label):
        """Retrieves the content of a document with a specific page label.

        Args:
            documents: A list of Document objects.
            target_page_label: The desired page label (e.g., '4').

        Returns:
            The page content if found, otherwise None.
        """
        for document in documents:
            if document.metadata['page_label'] == target_page_label:
                return document.page_content
        return None  # Return None if not found

    def get_related_page_docs(self,pdf_documents,filtered_list):
        """Create a string containing only the related documents from the filtered page"""
        related_page_docs=''
        for page in filtered_list:
            content = self.get_content_by_page_label(pdf_documents, page)
            related_page_docs+=content+'\n'
        return related_page_docs

    def convert_to_json(self,response) -> List[Dict]:
        """Convert the response to json containing actual section and filename"""
        try:
            data = json.loads(response)
            return {"sections":data["sections"],"filename":data["filename"]}

        except json.JSONDecodeError as e:
            print("Something went wrong...",e)
            return [{"title":"Something went wrong"}]

    def generate_slides_answer(self,question,related_page_docs):
        """Generate slides from the related documents"""
        response=ChatPromptTemplate(
                messages=[
                    SystemMessagePromptTemplate.from_template(slides_prompt),
                ],
                input_variables=["question", "context"],
            ) | self.llm

        return response.invoke({"question":question,"context":related_page_docs}).content

    def generate_web_slides_answer(self,question):
        """Generate slides from the llm"""
        response=ChatPromptTemplate(
                messages=[
                    SystemMessagePromptTemplate.from_template(web_prompt),
                ],
                input_variables=["question"],
            ) | self.llm

        return response.invoke({"question":question}).content

def format_json_response(json_answer: List[Dict]) -> str:
    """
    Format JSON response into a readable markdown string
    
    Args:
        json_answer (List[Dict]): Parsed JSON response
    
    Returns:
        str: Formatted markdown response
    """
    if not json_answer:
        return "No relevant information found."
    
    formatted_response = ""
    
    # Add title if exists
    title_section = next((item for item in json_answer if 'title' in item), None)
    if title_section:
        formatted_response += f"**{title_section['title']}**\n\n"
    
    # Process headers and content
    for section in json_answer:
        if 'header' in section:
            formatted_response += f"**{section['header']}**\n\n"
            
            # Handle points
            if 'points' in section:
                for point in section['points']:
                    formatted_response += f"- {point}\n"
                formatted_response += "\n"
            
            # Handle paragraph
            if 'paragraph' in section:
                formatted_response += f"{section['paragraph']}\n\n"
    
    return formatted_response

def create_pptx_download_link(json_answer: List[Dict]) -> str:
    """Generate PowerPoint and create Streamlit download button"""
    # Generate PowerPoint
    filename=json_answer["filename"]+'.pptx'
    print(filename)
    generate_ppt(json_answer["sections"],filename)

    # Read the file
    with open(filename, 'rb') as f:
        bytes = f.read()
    
    # Create download button
    st.download_button(
        label="Download Slides",
        data=bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    
    # Optional: Remove temporary file
    os.remove(filename)

def is_valid_response(json_answer: Optional[List[Dict]]) -> bool:
    """
    Validate the JSON answer to ensure it's a meaningful response.
    
    Args:
        json_answer (Optional[List[Dict]]): The JSON response to validate
    
    Returns:
        bool: True if the response is valid, False otherwise
    """
    if not json_answer:
        return False
    
    # Check if the first section contains a title
    title_section = next((item for item in json_answer if 'title' in item), {})

    title = title_section.get('title', '')
    
    # Check conditions for invalid response
    invalid_phrases = [
        "something went wrong",
        "don't know", 
        "cannot find", 
        "no information", 
        "unable to answer", 
        "not specified in the document"
    ]
    
    return not any(phrase in title.lower() for phrase in invalid_phrases)

def main():
    st.set_page_config(page_title="PDF Chat & Slide Generator", page_icon="📄")
    st.title("📄 PDF Chat & Slide Generator")

    # Initialize session state
    if 'generator' not in st.session_state:
        st.session_state.generator = PDFSlideGenerator()
    if 'pdf_documents' not in st.session_state:
        st.session_state.pdf_documents = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Sidebar for PDF upload
    with st.sidebar:
        st.header("Upload PDF")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        
        if uploaded_file is not None:
            with st.spinner("Processing PDF..."):
                st.session_state.pdf_documents = st.session_state.generator.load_pdf(uploaded_file)
                st.success("PDF processed successfully!")

    # Main chat interface
    st.header("Chat with Your PDF")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Ask a question about your PDF", disabled=not st.session_state.pdf_documents):
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process PDF and generate response
        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                # Generate relevant pages
                context = st.session_state.generator.generate_relevant_pages(prompt, st.session_state.pdf_documents)

                filtered_list = st.session_state.generator.filter_list(context)
                if(len(filtered_list)>0):
                # Get related page documents
                    related_page_docs = st.session_state.generator.get_related_page_docs(st.session_state.pdf_documents, filtered_list)
                    
                    # Generate slide answer
                    slide_answer = st.session_state.generator.generate_slides_answer(prompt, related_page_docs)
                    
                    # Convert to JSON
                    json_answer = st.session_state.generator.convert_to_json(slide_answer) if slide_answer else None
               
                # Format and display response
                    if json_answer and is_valid_response(json_answer):
                        formatted_response = format_json_response(json_answer["sections"])
                        st.markdown(formatted_response)

                        # Slide download option
                        download_link = create_pptx_download_link(json_answer)
                        if download_link:
                            st.markdown(download_link, unsafe_allow_html=True)
                else:
                    st.warning("No relevant information found in PDF. Searching web...")
                    web_answer = st.session_state.generator.generate_web_slides_answer(prompt)
                    json_answer = st.session_state.generator.convert_to_json(web_answer) if web_answer else None
                   
                    if json_answer and is_valid_response(json_answer):
                         formatted_response = format_json_response(json_answer["sections"])
                         st.markdown(formatted_response)

                        # Slide download option
                         download_web_link = create_pptx_download_link(json_answer)
                         if download_web_link:
                            st.markdown(download_link, unsafe_allow_html=True)
                    else:
                        st.write("Could not find information in PDF or web search.")
                        st.session_state.last_json_answer = None

        # Add assistant response to chat history
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": formatted_response if ((json_answer and is_valid_response(json_answer)) )  else "No relevant information found."
        })

if __name__ == "__main__":
    main()