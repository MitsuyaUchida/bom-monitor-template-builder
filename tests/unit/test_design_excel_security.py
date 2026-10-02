from bom_monitor_builder.design_excel.security import mask_secret_text, mask_secrets_in_mapping


def test_mask_secret_text_masks_inline_passwords() -> None:
    value = "user=admin -pw:secret123 token=abcdef"

    masked = mask_secret_text(value, ["password", "token"])

    assert "-pw:****" in masked
    assert "token=****" in masked


def test_mask_secrets_in_mapping_masks_secret_keys() -> None:
    values = {"password_field": "abc", "comment": "safe"}

    masked = mask_secrets_in_mapping(values, ["password"])

    assert masked["password_field"] == "****"
    assert masked["comment"] == "safe"


def test_mask_secret_text_masks_cli_style_flags() -> None:
    value = "--password secret123 -user admin --client-secret abcdef"

    masked = mask_secret_text(value, ["user", "password", "client-secret"])

    assert "--password ****" in masked
    assert "-user ****" in masked
    assert "--client-secret ****" in masked
