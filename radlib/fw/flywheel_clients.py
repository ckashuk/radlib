import flywheel


def uw_client():
    return flywheel.Client('wisc.fw.io:djEELpf52L5U5_Y21mzsVaSZ15uDpNOmrY24OPbXqp6GLGGACWyxmSZSA',
                           request_timeout=1000)

def uwhealth_client():
    return flywheel.Client('flywheel.uwhealth.org:djEj5E3OpCZiSj9p2uN_mqylHwaxGe7TewSklvXnKny9WiT1O9Y9Wgjgg',
                           request_timeout=1000)

def uwhealthaz_client():
    return flywheel.Client('flywheelaz.uwhealth.org:djEfiALy55nFsQ99M4E6ZQAW8F53fYucPUqU8HQhlZ4dBfsWZ-BYOcpCQ',
                           request_timeout=1000)


if __name__ == "__main__":
    # x = uw_client()
    y = uwhealth_client()
    z = uwhealthaz_client()

