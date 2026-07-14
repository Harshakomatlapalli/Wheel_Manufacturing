
def calculate_machinesetup_time(from_family, to_family):
    if from_family == to_family:
        if to_family == "Family_A":
            return 0
        if to_family == "Family_B":
            return 0
        if to_family == "Family_C":
            return 0
    if from_family == "Family_A" and to_family in ["Family_B","Family_C"]:
        if to_family == "Family_B":
            return 25
        if to_family == "Family_C":
            return 35
    if from_family == "Family_B" and to_family in ["Family_A", "Family_C"]:
        if to_family == "Family_A":
            return 25
        if to_family == "Family_C":
            return 35
    if from_family == "Family_C" and to_family in ["Family_A", "Family_B"]:
        if to_family == "Family_A":
            return 35
        if to_family == "Family_B":
            return 35
    return 0

class plantAssetstate:
    def __init__(self):
        self.last_family_casting_machine = {i : None for i in range(34)}
        self.last_family_on_machining = {i : None for i in range(7)}

        self.casting_machine_available = {i : True for i in range(34)} #Means Casting machine available- When casting is produced is completed always machine should be available
        self.machining_available = {i : True for i in range(7)}
