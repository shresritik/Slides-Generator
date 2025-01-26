relevant_page_prompt="""
    You are given a piece of text and a question. Please determine whether
    the question is related to the text.

    IMPORTANT:
    Before providing the answer please verify the piece of text and page number STRICTLY is related to the question.
    
    If it is related classify then generate only its page number, else don't generate anything
    The text: {text}
    question: {question}
    related page: {page}

    Answer: {page}
    """

slides_prompt= """
    As a presentation slide generator, use the following pieces of context to generate the slide and its filename without any extension.
    IMPORTANT:
    If the question or prompt asks to use your knowledge then please use your knowledge also.

    The file name should be related to the context.
    The slides should be precise and concise and can have title which is the main title, header which is the section header for the title,
    bullet points which are the main points for the header and paragraph which is the main paragraph for the header.

    IMPORTANT:
    At the end of the slide generate a conclusion also with "Conclusion" as the header with the summary of the context as paragraph or bullet points.

    Based on these three sections (title, header, bullet points and paragraph) generate the slides in json format.

    The title should be treated as separate dictionary and should not come with headers, bullet points and paragraphs.

    IMPORTANT:
    Also end the slide with a quote related to the context and make its key as the title at the end of the slide.

    IMPORTANT:
    The input variables are in single curly braces

    The output format should be in json format like:

    {{ sections:[{{
    title:"<title>"
    }},
    {{
    header:"<header>"
    points:["","",""]
    }},
    {{
    header:"<header>"
    paragraph:"<paragraph>"
    }},
    {{
    title:"<quote>"
    }},
    ],filename:""}}

    {context}
    Question: {question}
    Helpful Answer:"""

web_prompt= """
    As a presentation slide generator, use the following pieces of context to generate the slide and its filename without any extension.

    IMPORTANT:
    If the pdf context does not provide any information to answer the question, just use you knowledge.

    The file name should be related to the context.
    The slides should be precise and concise and can have title which is the main title, header which is the section header for the title,
    bullet points which are the main points for the header and paragraph which is the main paragraph for the header.

    IMPORTANT:
    At the end of the slide generate a conclusion also with "Conclusion" as the header with the summary of the context as paragraph or bullet points.

    Based on these three sections (title, header, bullet points and paragraph) generate the slides in json format.

    The title should be treated as separate dictionary and should not come with headers, bullet points and paragraphs.

    Also end the slide with a quote related to the context and make it the title at the end of the slide.

    IMPORTANT:
    The input variables are in single curly braces.

    The output format should be in json format like:

    {{ sections:[{{
    title:"<title>"
    }},
    {{
    header:"<header>"
    points:["","",""]
    }},
    {{
    header:"<header>"
    paragraph:"<paragraph>"
    }},
    {{
    title:"<quote>"
    }},
    ],filename:""}}


    Question: {question}
    Helpful Answer:"""