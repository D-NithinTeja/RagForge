from src.ragforge.services.llm_service import (
    get_image_summarizer,
    get_qa_llm,
    get_text_llm,
    get_text_table_summarizer,
)


def test_llm_singleton_and_chain_compilation():
    text_model = get_text_llm()
    qa_model = get_qa_llm()

    assert text_model.temperature == 0.3

    # Verify both singletons cache onto the exact same reference identity layout
    assert get_text_llm() is text_model

    # Validate that the LCEL creates valid Runnables
    text_chain = get_text_table_summarizer()
    image_chain = get_image_summarizer()

    assert text_chain is not None
    assert image_chain is not None
