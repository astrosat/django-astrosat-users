"""
   _____            __                               __
  /  _  \   _______/  |________  ____  ___________ _/  |_
 /  /_\  \ /  ___/\   __\_  __ \/  _ \/  ___/\__  \\   __\
/    |    \\___ \  |  |  |  | \(  <_> )___ \  / __ \|  |
\____|__  /____  > |__|  |__|   \____/____  >(____  /__|
        \/     \/                         \/      \/
 ____ ___
|    |   \______ ___________  ______
|    |   /  ___// __ \_  __ \/  ___/
|    |  /\___ \\  ___/|  | \/\___ \
|______//____  >\___  >__|  /____  >
             \/     \/           \/
"""


APP_NAME = "astrosat_users"

VERSION = (1, 0, 1)

__title__ = "django-astrosat-users"
__author__ = "Allyn Treshansky"
__version__ = ".".join(map(str, VERSION))

default_app_config = "astrosat_users.apps.AstrosatUsersConfig"
