import pytest
from flask import url_for
from flask_security import url_for_security
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


@pytest.mark.usefixtures("live_server")
def test_login(driver):
    driver.get(url_for_security('login', _external=True))
    email = driver.find_element(By.NAME, 'email')
    password = driver.find_element(By.NAME, 'password')

    email.clear()
    email.send_keys("admin")
    password.clear()
    password.send_keys("admin" + Keys.RETURN)

    assert "Response Rate Dashboard" in driver.title

@pytest.mark.usefixtures("live_server")
def test_logout(driver):
    driver.get(url_for("dashboard.index", _external=True))
    assert "Response Rate Dashboard" in driver.title

    settings = driver.find_element(By.LINK_TEXT, 'Settings')
    settings.click()
    logout = driver.find_element(By.LINK_TEXT, 'Logout')
    logout.click()
    assert "User Sign In" in driver.title

    driver.get(url_for("dashboard.index", _external=True))
    assert "User Sign In" in driver.title
