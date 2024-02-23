"""Pytest for basic KItem connection properties"""
import pytest
import responses


@responses.activate
def test_kitem_basic(custom_address, get_mock_kitem_ids):
    """Test KItem properties"""

    from dsms.core.configuration import Configuration
    from dsms.core.context import Context
    from dsms.core.dsms import DSMS
    from dsms.knowledge.kitem import KItem

    assert Context.dsms is None

    with pytest.warns(UserWarning, match="No authentication details"):
        dsms = DSMS(host_url=custom_address)

    instance = KItem(
        id=get_mock_kitem_ids[0],
        name="foo123",
        ktype_id=dsms.ktypes.Organization,
    )

    assert isinstance(instance.dsms, DSMS)
    assert isinstance(instance.dsms.config, Configuration)
    assert Context.dsms == instance.dsms


@responses.activate
def test_kitem_config_class(custom_address, get_mock_kitem_ids):
    """Test KItem properties"""

    from dsms.core.configuration import Configuration
    from dsms.core.context import Context
    from dsms.core.dsms import DSMS
    from dsms.knowledge.kitem import KItem

    assert Context.dsms is None

    with pytest.warns(UserWarning, match="No authentication details"):
        config = Configuration(host_url=custom_address)
        dsms = DSMS(config=config)

    instance = KItem(
        id=get_mock_kitem_ids[0],
        name="foo123",
        ktype_id=dsms.ktypes.Organization,
    )

    assert isinstance(instance.dsms, DSMS)
    assert config == instance.dsms.config
    assert Context.dsms == instance.dsms


@responses.activate
def test_bad_config_kwargs(custom_address):
    from dsms import DSMS, Configuration

    with pytest.warns(UserWarning, match="No authentication details"):
        config = Configuration(host_url=custom_address)

    with pytest.raises(
        ValueError, match="`config`-keyword is defined among others."
    ):
        DSMS(host_url=custom_address, config=config)


@responses.activate
def test_kitem_custom_config_env(custom_address, get_mock_kitem_ids):
    import os

    from dsms.core.dsms import DSMS
    from dsms.knowledge.kitem import KItem

    os.environ["DSMS_HOST_URL"] = custom_address

    with pytest.warns(UserWarning, match="No authentication details"):
        dsms = DSMS()

    custom_instance = KItem(
        id=get_mock_kitem_ids[0],
        name="foo123",
        ktype_id=dsms.ktypes.Organization,
    )

    assert str(custom_instance.dsms.config.host_url) == custom_address

    os.environ.pop("DSMS_HOST_URL")


@responses.activate
def test_dsms_bad_object():
    from dsms.core.dsms import DSMS

    bad_object = "hello world"

    with pytest.raises(TypeError, match="The passed config-kwarg with value"):
        DSMS(config=bad_object)


@responses.activate
def test_kitem_bad_kwarg(get_mock_kitem_ids, custom_address):
    from pydantic import ValidationError

    from dsms.core.dsms import DSMS
    from dsms.knowledge.kitem import KItem

    with pytest.warns(UserWarning, match="No authentication details"):
        dsms = DSMS(host_url=custom_address)

    with pytest.raises(ValidationError):
        KItem(
            id=get_mock_kitem_ids[0],
            name="foo123",
            foo="bar",
            ktype_id=dsms.ktypes.Organization,
        )


@responses.activate
def test_kitem_connection_error():
    from dsms.core.configuration import Configuration
    from dsms.core.dsms import DSMS

    bad_url = "https://www.bad-dsms-instance.org"

    with pytest.warns(UserWarning, match="No authentication details"):
        bad_config = Configuration(host_url=bad_url)

    with pytest.raises(ConnectionError, match="Invalid DSMS instance:"):
        DSMS(config=bad_config)


@responses.activate
def test_kitem_default_ktypes(custom_address):
    from dsms.core.dsms import DSMS

    with pytest.warns(UserWarning, match="No authentication details"):
        dsms = DSMS(host_url=custom_address)

    assert len(dsms.ktypes) == 1


@responses.activate
def test_ktype_property(get_mock_kitem_ids, custom_address):
    from dsms.core.context import Context
    from dsms.core.dsms import DSMS
    from dsms.knowledge.kitem import KItem

    with pytest.warns(UserWarning, match="No authentication details"):
        dsms = DSMS(host_url=custom_address)

    kitem = KItem(
        id=get_mock_kitem_ids[0],
        name="foo123",
        ktype_id=dsms.ktypes.Organization,
    )

    assert kitem.ktype == Context.ktypes.get(dsms.ktypes.Organization.value)
