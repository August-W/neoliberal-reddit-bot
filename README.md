# neoliberal-shill-bot
___________________


This server-less bot runs data analytics on /r/neoliberal, on the Discussion Thread from the previous day.
__________________________________________________________________________________


# SETUP
1. Install python
2. Download this project
3. Create a new Reddit account for this bot. Go to https://www.reddit.com/prefs/apps/ to create the bot.
4. Take note of the bot's Client ID and Client Secret. They look like this: https://i1.wp.com/pythonforengineers.com/wp-content/uploads/2014/11/redditbot2.jpg
5. Edit the values in .sample-env in this project with the Client ID, Client Secret, and the username and password for your bot's account.
6. Using the command prompt / terminal, navigate to this project's folder and run:

python setup.py        

This should create the .env file you need to run this bot, based on .sample-env.
7. Using the command prompt / terminal, install all required dependencies

_____________________________________________________________________________________


# RUN THE BOT  
Using the command prompt / terminal, navigate to this project's folder and run:

python app.py

Even if you run it multiple times, the bot will not post more than one time for each Discussion Thread.
_____________________________________________________________________________________


# I SUGGEST SETTING THIS BOT TO RUN ON BOOT
This way, the bot will visit reddit daily and notify you on new manga, and you don't have to manually run it each time. The bot tries to read every post that has been uploaded since the last post it read. This means that, the less frequently you run the bot, the more posts it has to read. If you run the bot very infrequently (e.g. once every two months or something), it may time out before it reads every post.

# TO RUN ON BOOT (WINDOWS):
1. Using any text editor, create a .bat file (the filename doesn't matter) with the following line:

python C:/{PATH_TO_YOUR_DIRECTORY}/app.py

Replacing {PATH_TO_YOUR_DIRECTORY} with the path to this project on your computer
2. Follow these steps to add this .bat file to your startup folder: https://www.computerhope.com/issues/ch000322.htm

3. Create environment variables for the .env values (CLIENT_ID, CLIENT_SECRET, etc.): https://msdn.microsoft.com/en-us/library/windows/desktop/ms682653%28v=vs.85%29.aspx

# TO RUN ON BOOT (LINUX/MAC):
 Same basic idea, but with a bash script (.sh, not .bat).
___________________________________________________________________________________