import os
import sys
import time
import random
import subprocess
from typing import List, Optional
from dataclasses import dataclass

import requests
from seleniumbase import SB

@dataclass
class StreamerInfo:
    """Represents a streamer with their username and platform URL."""
    username: str
    platform_url: str

class StreamStatusChecker:
    """
    Provides methods for checking stream status on different platforms.
    """

    TWITCH_CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"  # Publicly known Client-ID for Twitch

    @staticmethod
    def is_twitch_online(username: str) -> bool:
        """
        Returns True if the Twitch stream is online, False otherwise.
        Uses the public frontend Client-ID (no OAuth).
        """
        url = f"https://www.twitch.tv/{username}"
        headers = {"Client-ID": StreamStatusChecker.TWITCH_CLIENT_ID}
        resp = requests.get(url, headers=headers)
        return "isLiveBroadcast" in resp.text

class CaptchaHandler:
    """
    Handles CAPTCHA interactions on streaming sites using SeleniumBase.
    """

    def __init__(self, driver):
        self.driver = driver

    def handle_captcha(self):
        """Clicks and handles CAPTCHA if present."""
        self.driver.uc_gui_click_captcha()
        self.driver.sleep(1)
        self.driver.uc_gui_handle_captcha()
        self.driver.sleep(4)

class StreamBot:
    """
    Main bot class for automating stream interaction and monitoring.
    """

    def __init__(self, streamer: StreamerInfo):
        self.streamer = streamer

    def open_stream_and_handle_popups(self, driver, reconnect_time: int = 4):
        """
        Opens the stream in the browser, handles CAPTCHAs and popups like 'Accept' buttons.
        """
        driver.uc_open_with_reconnect(self.streamer.platform_url, reconnect_time)
        driver.sleep(4)
        captcha = CaptchaHandler(driver)
        captcha.handle_captcha()
        # Handle Accept button popup if present
        if driver.is_element_present('button:contains("Accept")'):
            driver.uc_click('button:contains("Accept")', reconnect_time=4)

    def monitor_kick_stream(self, driver):
        """
        Monitors the Kick.com stream and reopens the stream in a new driver if the player is visible.
        """
        if driver.is_element_visible('#injected-channel-player'):
            new_driver = driver.get_new_driver(undetectable=True)
            self.open_stream_and_handle_popups(new_driver, reconnect_time=5)
            driver.sleep(10)
            if new_driver.is_element_present('button:contains("Accept")'):
                new_driver.uc_click('button:contains("Accept")', reconnect_time=4)
            # Wait while the player is visible
            while driver.is_element_visible('#injected-channel-player'):
                driver.sleep(10)
            driver.quit_extra_driver()

    def monitor_twitch_stream(self, driver):
        """
        Monitors the Twitch stream if online, handling popups and CAPTCHA as needed.
        """
        if StreamStatusChecker.is_twitch_online(self.streamer.username):
            twitch_url = f"https://www.twitch.tv/{self.streamer.username}"
            driver.uc_open_with_reconnect(twitch_url, 5)
            if driver.is_element_present('button:contains("Accept")'):
                driver.uc_click('button:contains("Accept")', reconnect_time=4)
            new_driver = driver.get_new_driver(undetectable=True)
            new_driver.uc_open_with_reconnect(twitch_url, 5)
            driver.sleep(10)
            if new_driver.is_element_present('button:contains("Accept")'):
                new_driver.uc_click('button:contains("Accept")', reconnect_time=4)
            # The following input_field is undefined, but preserved for logic integrity.
            # Uncomment and define input_field if applicable.
            # while driver.is_element_visible(input_field):
            #     driver.sleep(10)
            driver.quit_extra_driver()

    def run(self):
        """
        Runs the automation sequence for Kick and Twitch monitoring.
        """
        with SB(uc=True, test=True) as driver:
            self.open_stream_and_handle_popups(driver, reconnect_time=4)
            self.monitor_kick_stream(driver)
            driver.sleep(1)
            self.monitor_twitch_stream(driver)
            driver.sleep(1)

# Example usage:
def main():
    """
    Entry point for running the stream bot.
    """
    streamer = StreamerInfo(username="brutalles", platform_url="https://kick.com/brutalles")
    bot = StreamBot(streamer)
    bot.run()

if __name__ == '__main__':
    main()
