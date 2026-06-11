from unstructured.documents.elements import CompositeElement, Image, Table

from src.ragforge.services.chunk_service import extract_images_base64, separate_elements


def test_element_separation_logic():
    # 1. Setup mock data
    flat_text = CompositeElement(text="Lorem ipsum")
    standalone_table = Table(text="Column1,Column2\nVal1,Val2")
    composite_text_table = CompositeElement(text="Container")
    composite_text_table.metadata.orig_elements = [standalone_table]

    mixed_elements = [flat_text, standalone_table, composite_text_table]

    # 2. Execute target function sweep
    texts, tables = separate_elements(mixed_elements)

    # 3. Assert correct array distribution boundaries
    assert len(texts) == 2  # flat_text and composite_text_table
    assert len(tables) == 2  # standalone_table and the unpacked standalone_table

    assert flat_text in texts
    assert composite_text_table in texts

    assert standalone_table in tables


def test_standalone_image_extraction_safeguards():
    elements_without_images = [Image(text="Flat Data Table")]
    images = extract_images_base64(
        elements_without_images
    )  # Ignore the warning from Pylance
    assert images == []
