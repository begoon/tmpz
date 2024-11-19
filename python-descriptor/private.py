class PrivateField:
    def __init__(self, value):
        self._value = value

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if instance._inside:
            return self._value
        raise AttributeError("can't get private attribute")
    
    def __set__(self, value):
        raise AttributeError("can't set private attribute")
    
    def private_get(self):
        return self._value

    
class A:
    def __init__(self):
        self._inside = False
        
    member_x = PrivateField(500)

    def accessor_x(self):
        self._inside = True
        try:
            return self.member_x
        finally:
            self._inside = False

a = A()
print("a.x = ", a.accessor_x())
print()
print(a.member_x) # AttributeError: can't get private attribute
