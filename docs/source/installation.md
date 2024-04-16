# Installation and Setup Guide
How to install and setup the dsms-python-sdk.



## 1.1. Installation
Install in your  folder (or any folder you like).

- `git clone git@github.com:MI-FraunhoferIWM/dsms-python-sdk.git`
- `cd dsms-python-sdk`
- `pip install .`

## 1.2. Additional Setup
You need to authenticate yourself to connect with dsms-core using dsms-python-sdk.

Therefore follow the following process:
1. Pick the DSMS host of your choice and
2. How to get the token
Step 1: Login into the selected data.space instance of your choice.

![copy_token_1](assets/images/copy_token_1.jpg)

Step 2: Enter your credentials

![copy_token_2](assets/images/copy_token_2.jpg)

Step 3: After logging in you will land up in the home page. Now look at the my profile option

![copy_token_3](assets/images/copy_token_3.jpg)

Step 4: The my profile option should look something like below. Now click on the Advanced.

![copy_token_4](assets/images/copy_token_4.jpg)

Step 5: The Advanced section should like the below. Now click on the copy token to clipboard

![copy_token_6](assets/images/copy_token_5.jpg)

Step 6: Now paste it in DSMS_TOKEN attribute of the .env file in root/dsms-python-sdk.

Now you are ready to use dsms-sdk. Do check out the tutorials section to try out on some basic examples on how to use dsms-sdk.
