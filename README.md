# zoozl

Server for chatbot services

## Usage

For basic example a chatbot plugin is provided in `zoozl.plugins` package. It is a simple chatbot that allows to play bulls & cows game. It is also a plugin that is loaded in case no configuration file is provided.

### Run websocket server

```bash
python -m zoozl 1601 --conf chatbot.toml
```
where `1601` is the port number and `chatbot.toml` is optional configuration file.

## Architecture

zoozl package contains modules that handle various input interfaces like websocket or http POST and a chatbot interface that must be extended by plugins. Without plugin zoozl is not able to respond to any input. Plugin can be considered as a single chat assistant to handle a specific task. Plugin can be huge and complex or simple and small. It is up to the developer to decide how to structure plugins.
![zoozl_package](docs/images/zoozl_package.svg)


## Plugin

### Mimimal setup

1. Add in toml configuration
```
extensions = ['my_plugin_module']
```
2. Make sure `my_plugin_module` is importable from within python that will run zoozl server
3. Create file `my_plugin_module.py`
```
from zoozl.chatbot import Interface

class MyPlugin(Interface):

    aliases = ("call myplugin",)

    def consume(self, context: , package: Package):
        package.callback("Hello this is my plugin response")
```
4. Start zoozl server with your configuration file and asking to bot `call myplugin` it will respond `Hello this is my plugin response`

### Configuration file

Configuration file must conform to TOML format. Example of configuration:
```
title = "Global configuration for Chatbot"
extensions = ["chatbot_fifa_extension", "zoozl.plugins.greeter"]

[chatbot_fifa_extension]
database_path = "tests/tmp"
administrator = "admin"
```

Root objects like title, extensions are configuration options for chatbot system wide setup, you can pass unlimited objects in configuration, however suggested is to add a component for each plugin and separate those within components.


* TODO: Describe plugin interface and creation
* TODO: Add authentication and authorization interaction between chatbot and plugin
