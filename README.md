# Dragon Bot

Dragon Bot is a Discord bot designed to help manage my server and provide some fun and useful commands. It's built with Python using the `discord.py` library and is constantly evolving with new features.

## How to Use

All commands are available as slash commands. Simply type `/` in your Discord server to see a list of available commands and their descriptions.

## Setup for Development

To run Dragon Bot on your own machine for development purposes, follow these steps:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/DragonSenseiGuy/dragon-bot
    cd dragon-bot
    ```

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file**:
    Create a file named `.env` in the root of the project and add your bot token:
    ```
    BOT_TOKEN=your_bot_token_here
    ```

5.  **Run the bot**:
    ```bash
    python3 main.py
    ```

## Contributing

Contributions are welcome! If you have any ideas for new features or find any bugs, feel free to open an issue or submit a pull request.
