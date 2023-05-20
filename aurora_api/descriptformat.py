
class DescFormatter:
    def __init__(self,summary):
        self.summary = summary
    
    def skeleton(self):
        if self.summary.__contains__('child registration'):
            return ['Appointment Time', 'Booked By','Relationship To Child', "Child's Name", "Child's DOB", "Child's Gender",'Place of Birth', "Parents Name(s)"]