## reising oop cause why not


class Friend:
    def __init__(self,name,gender, ranking):
        self.name=name
        self.gender=gender
        self.ranking=ranking

    def be_nice(self):
        return f"{self.name} is being nice!"
    def __str__(self):
        return f"Name: {self.name}, Gender: {self.gender}"
    
    def __repr__(self):
        return f"Friend(name={self.name},gender={self.gender},ranking={self.ranking})"
    
Sho= Friend("Shoghi","Male",2)
Bethel=Friend("Cherish","Female",4)
Tolani=Friend("Tolani","Male",1)


print(repr(Sho))
print(Bethel)
    

