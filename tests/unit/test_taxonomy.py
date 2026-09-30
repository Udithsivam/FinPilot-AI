from src.categorization.taxonomy import TAXONOMY, joint_labels, split_joint_label, subcategories, top_level_categories


def test_top_level_categories_match_taxonomy_keys():
    assert set(top_level_categories()) == set(TAXONOMY.keys())


def test_subcategories_match_taxonomy():
    assert set(subcategories("Food")) == set(TAXONOMY["Food"].keys())


def test_subcategories_of_unknown_category_is_empty():
    assert subcategories("Not A Category") == []


def test_joint_labels_cover_every_subcategory():
    expected = {f"{cat} > {sub}" for cat, subs in TAXONOMY.items() for sub in subs}
    assert set(joint_labels()) == expected


def test_split_joint_label_roundtrip():
    for label in joint_labels():
        category, subcategory = split_joint_label(label)
        assert f"{category} > {subcategory}" == label
        assert category in TAXONOMY
        assert subcategory in TAXONOMY[category]
