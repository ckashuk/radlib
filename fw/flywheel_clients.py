import flywheel

# 202504 csk "python_programming" API key good on all three instances until Apr 5, 2026
def uw_client():
    # key 'api' generated 6/26/2025 expires 6/26/2028
    return flywheel.Client('wisc.flywheel.io:djEgK2HwN5LXLwegKoAGbGxhuD57hP2NZSa_IqNV0G1KRSOUSC5RkOHbA',
                           request_timeout=1000)

def uwhealth_client():
    return flywheel.Client('flywheel.uwhealth.org:djEuivnQM1ByLmqHFku7aKfKsJaVVq5u1ulsRIcbzkx0LOINiIPnx7orw',
                           request_timeout=1000)

def uwhealthaz_client():
    return flywheel.Client('flywheelaz.uwhealth.org:djEfiALy55nFsQ99M4E6ZQAW8F53fYucPUqU8HQhlZ4dBfsWZ-BYOcpCQ',
                           request_timeout=1000)


if __name__ == "__main__":
    # 202504 csk quick check that all three are active (should throw no exceptions)
    x = uw_client()
    y = uwhealth_client()
    z = uwhealthaz_client()

