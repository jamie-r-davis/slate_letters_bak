import requests


def get_external_session(hostname, username, password):
    """Returns an authenticated session for an external user.

    Parameters
    ----------
    hostname : str
        The hostname of the slate environment to use, including protocol (eg, https://slateuniversity.net)
    username : str
        The username to use for authentication
    password : str
        The password to use for authentication
    """
    url = f"{hostname}/manage/login?cmd=external"
    s = requests.session()
    s.headers.update({"Origin": hostname})
    r1 = s.get(url)
    r2 = s.post(r1.url, data={"user": username, "password": password})
    r2.raise_for_status()
    return s
