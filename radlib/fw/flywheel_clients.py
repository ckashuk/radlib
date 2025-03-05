import flywheel


def uw_client():
    return flywheel.Client('wisc.fw.io:djEELpf52L5U5_Y21mzsVaSZ15uDpNOmrY24OPbXqp6GLGGACWyxmSZSA',
                           request_timeout=1000)

def uwhealth_client():
    return flywheel.Client('flywheel.uwhealth.org:djELg8PTxfE8uGAtoFwzfsgJKe5FAbyeETESNB20c1t-MbH8C27gOGWKQ',
                           request_timeout=1000)

def uwhealthaz_client():
    return flywheel.Client('flywheelaz.uwhealth.org:djESGL039D5xmVq81ZknQS4tT2nEg2IYNcd3z-ubX_3wzwCyLaUJ1WeAg',
                           request_timeout=1000)

