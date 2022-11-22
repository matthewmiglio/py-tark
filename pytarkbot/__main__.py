import sys
import time
from typing import Union

import pyautogui
import pyperclip
import PySimpleGUI as sg
from pytarkbot.caching import check_user_settings, read_user_settings

from pytarkbot.client import intro_printout, orientate_terminal
from pytarkbot.dependency import get_bsg_launcher_path, setup_tesseract
from pytarkbot.flee import (
    get_price_2,
    get_price_undercut,
    get_to_flee_tab,
    get_to_flee_tab_from_my_offers_tab,
    get_to_my_offers_tab,
    orientate_add_offer_window,
    post_item,
    remove_offers,
    select_random_item_to_flee,
    set_flea_filters,
    wait_till_can_add_another_offer,
)
from pytarkbot.launcher import restart_tarkov
from pytarkbot.logger import Logger

pyautogui.FAILSAFE = False

# setup dependency paths
bsg_launcher_path = get_bsg_launcher_path()
setup_tesseract()


logger = Logger()


def flea_items_main():
    state = "intro"
    while True:
        if state == "intro":
            state_intro()
            state = "flee_mode"

        if state == "restart":
            state_restart()
            state = "flee_mode"

        if state == "flee_mode":
            state = state_flea_mode()

        if state == "remove_flee_offers":
            state = state_remove_flee_offers()


def state_intro():
    blank_line = "////////////////////////////////////////////////////"
    logger.log("")
    logger.log(blank_line)
    logger.log("State==Intro")
    logger.log(blank_line)
    logger.log("")

    restart_tarkov(logger, bsg_launcher_path)


def state_remove_flee_offers():
    blank_line = "////////////////////////////////////////////////////"
    logger.log("")
    logger.log(blank_line)
    logger.log("State==Remove flee offers")
    logger.log(blank_line)
    logger.log("")

    logger.log("STATE=remove_flee_offers")

    logger.log("Getting to the flea tab.")
    if get_to_flee_tab(logger) == "restart":
        return "restart"

    logger.log("Getting to my offers tab")
    if get_to_my_offers_tab(logger) == "restart":
        return "restart"

    logger.log("Starting remove offers alg.")
    remove_offers(logger)

    logger.log("Returning to browse page in the flea.")
    get_to_flee_tab_from_my_offers_tab(logger)

    return "flee_mode"


def state_flea_mode():
    logger.log("Beginning flea alg.\n")
    while True:
        # open flea
        logger.log("Getting to flea")
        if get_to_flee_tab(logger) == "restart":
            return "restart"
        time.sleep(1)

        # wait for another add offer
        logger.log("Waiting for another flea offer slot.")
        if wait_till_can_add_another_offer(logger) == "remove_flee_offers":
            return "remove_flee_offers"
        time.sleep(1)

        # click add offer
        logger.log("Adding another offer.")
        pyautogui.moveTo(837, 82, duration=0.33)
        pyautogui.click()
        time.sleep(0.33)

        logger.log("Orientating add offer window.")
        orientate_add_offer_window(logger)
        time.sleep(1)
        orientate_add_offer_window(logger)
        time.sleep(1)

        select_random_item_to_flee(logger)
        time.sleep(1)

        # set flea filter
        logger.log("Setting the flea filters to only RUB/players only.")
        set_flea_filters(logger)
        time.sleep(1)

        # get/check price
        logger.log("Doing price check.")
        # logger.add_flea_sale_attempt()
        detected_price = get_price_2()
        if detected_price != None:
            logger.log(f"Price of {detected_price} passed check.")

            # get undercut
            undercut_price = get_price_undercut(detected_price)
            logger.log(f"Undercut price is: {undercut_price}")

            # post this item
            post_item(logger, undercut_price)
        logger.add_flea_sale_attempt()


def state_restart():
    blank_line = "////////////////////////////////////////////////////"
    for _ in range(5):
        logger.log(blank_line)
    logger.log("\n\nState==Restart")

    # add to logger
    logger.add_restart()

    restart_tarkov(logger, bsg_launcher_path)

    return "flee_mode"


def show_donate_gui():
    sg.theme("Material2")
    layout = [
        [
            sg.Text(
                "Paypal donate link: \n\nhttps://www.paypal.com/donate/?business=YE72ZEB3KWGVY&no_recurring=0&item_name=Support+my+projects%21&currency_code=USD"
            ),
            sg.Text(size=(15, 1), key="-OUTPUT-"),
        ],
        [sg.Button("Exit"), sg.Button("Copy link to clipboard")]
        # https://www.paypal.com/donate/?business=YE72ZEB3KWGVY&no_recurring=0&item_name=Support+my+projects%21&currency_code=USD
    ]
    window = sg.Window("PY-TarkBot", layout)
    while True:
        event, values = window.read()
        if event in [sg.WIN_CLOSED, "Exit"]:
            break

        if event == "Copy link to clipboard":
            pyperclip.copy(
                "https://www.paypal.com/donate/?business=YE72ZEB3KWGVY&no_recurring=0&item_name=Support+my+projects%21&currency_code=USD"
            )

    window.close()


def show_help_gui():
    out_text = (
        "Debugging Information\n\n"
        + "    1. If the bot is instantly closing after pressing the start button, it is likely due to an incorrectly specified launcher path @ appdata/roaming/py-tarkBot/config.json\n"
        + "        In this config file make sure to use double slashes as shown in the default launcher path.\n"
        + "    2. If youre getting '[WinError 5] Access is denied error', try running the program as administrator.\n"
        + "    3. If window resizing is your issue, try to start the tarkov client with a resolution smaller than 1280x960 (something like 1154x900).\n"
        + "    4. Hideout mode is WIP so dont even expect that mode to do anything right and keep this in mind when reporting glaring bugs with the hideout mode.\n"
        + "\n\nHideout Information:\n\n"
        + "     Workbench: Have M18 smokes and M67 nades for green gunpowder craft\n"
        + "     Medstation: Have AI-2s, bandages(blue and white ones), and augmentin\n"
        + "     Water collector: have extra water filters \n"
        + "     Scav case: Have intelligence folders \n"
        + "\n\nFlea Mode Information:\n\n"
        + "     Bot will sell the items in the top ~40 rows of your inventory.\n"
        + "     Make sure this area is composed of items only for the flea.\n"
        + "     This bot does well to not flea the wrong items, or to waste your money- but it is not perfect.\n"
        + "     The bot chooses an item, looks for its price, and if the price recognition is any bit unsure itll move onto the next one, otherwise it will sell it according to an undercut function.\n\n"
        + "You can share any failures (or successes?) of the bot on the github @ github.com/matthewmiglio/py-tarkBot\n"
    )

    sg.theme("Material2")
    layout = [
        [sg.Text(out_text)],
    ]
    window = sg.Window("PY-TarkBot", layout)
    while True:
        event, values = window.read()
        if event in [sg.WIN_CLOSED, "Exit"]:
            break
    window.close()


def main():
    orientate_terminal()
    intro_printout(logger)

    out_text = "" + "-Python Tarkov bot - Matthew Miglio ~Aug 2022\n\n"
    out_text += (
        "-You MUST manually set tarkov to windowed and 4:3 BEFORE running the bot.\n"
    )

    sg.theme("Material2")
    # defining various things that r gonna be in the gui.
    layout = [
        [sg.Text(out_text)],
        # buttons
        [sg.Button("Start"), sg.Button("Stop"), sg.Button("Help"), sg.Button("Donate")]
        # https://www.paypal.com/donate/?business=YE72ZEB3KWGVY&no_recurring=0&item_name=Support+my+projects%21&currency_code=USD
    ]
    # window layout
    window = sg.Window("PY-TarkBot", layout)
    # run the gui
    while True:
        # get gui vars
        event, values = window.read()
        # if gui sees close then close
        if event in [sg.WIN_CLOSED, "Exit"]:
            break
        # if gui sees start press then start bot
        if event == "Start":
            # if Flea mode checkbox is checked, run the Flea mode main
            window.close()
            logger.log("\n\nStarting flea snipe mode.\n")
            flea_items_main()

        if event == "Help":
            show_help_gui()

        if event == "Donate":
            show_donate_gui()

    window.close()


def end_loop():
    print("Press ctrl-c to close the program.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        sys.exit()


def read_window(
    window: sg.Window, timeout: int = 10
) -> tuple[str, dict[str, Union[str, int]]]:
    # Method for reading the attributes of the window
    # have a timeout so the output can be updated when no events are happening
    read_result = window.read(timeout=timeout)  # ms
    if read_result is None:
        print("Window not found")
        sys.exit()
    return read_result



def load_last_settings(window):
    if check_user_settings():
        read_window(window)  # read the window to edit the layout
        user_settings = read_user_settings()
        if user_settings is not None:
            for key in user_config_keys:
                if key in user_settings:
                    window[key].update(user_settings[key])
        window.refresh()  # refresh the window to update the layout




def main_gui():
    console_log = True  # enable/disable console logging

    window = sg.Window("Py-ClashBot", main_layout)

    load_last_settings(window)

    # track worker thread, communication queue and logger
    thread: Union[WorkerThread, None] = None
    statistics_q: Queue[dict[str, Union[str, int]]] = Queue()
    logger = Logger(statistics_q, console_log=console_log)

    # run the gui
    while True:
        event, values = read_window(window, timeout=10)

        if event in [sg.WIN_CLOSED, "Exit"]:
            # shut down the thread if it is still running
            shutdown_thread(thread)
            break

        if event == "Start":
            thread = start_button_event(logger, window, values)

        elif event == "Stop" and thread is not None:
            stop_button_event(logger, window, thread)
            # reset the logger and communication queue after thread has been stopped
            statistics_q = Queue()
            logger = Logger(statistics_q, console_log=console_log)

        elif event in user_config_keys:
            save_current_settings(values)

        elif event == "Donate":
            webbrowser.open(
                "https://www.paypal.com/donate/"
                + "?business=YE72ZEB3KWGVY"
                + "&no_recurring=0"
                + "&item_name=Support+my+projects%21"
                + "&currency_code=USD"
            )

        elif event == "Help":
            show_help_gui()

        elif event == "issues-link":
            webbrowser.open(
                "https://github.com/matthewmiglio/py-clash-bot/issues/new/choose"
            )

        update_layout(window, statistics_q)

    # shut down the thread if it is still running
    shutdown_thread(thread)

    window.close()



if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        end_loop()
