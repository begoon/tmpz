class ReadOnlyField:
    def __init__(self, value):
        self.value = value

    def __get__(self, instance, owner):
        return self.value
    
    def __set__(self, instance, value):
        raise AttributeError("can't set readonly attribute")
    
class A:
    member_x = ReadOnlyField(500)

a = A()
print(f"a.member_x =", a.member_x)
print()
a.member_x = 100 # AttributeError: can't set readonly attribute