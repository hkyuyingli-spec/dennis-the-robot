from nutribot.herbal_kitchen import validate_output


def test_rejects_herb_not_in_allowed_list():
    assert not validate_output({"herbs": ["ginger"]}, ["mint"])


def test_rejects_banned_claim_word():
    assert not validate_output({"herbs": ["mint"], "text": "Mint cures illness."}, ["mint"])
