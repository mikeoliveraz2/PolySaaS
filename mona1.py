print("Hello, World!")
print("I am learning Python")
#variables
name = "Alex"
age = 20
height = 1.75
print(name)
print(age)
print(height)
#you can use variables inside print with an f-string:
name = "Alex"
age = 20
print(f"My name is {name} and I am {age} years old.")
#Input from the keyboard
name = input("what is your name?")
print(f"Nice to meet you {name}")
#if you need a number, convert it with int():
age_text = input("How old are you?")
age = int(age_text)+1
print(f"Next year you will be {age }.")
#if then else
if True:
    print("True")
else:
    print("False")
#if then elif then else
if age > 18:
    print("You are an adult")
elif age == 18:
    print("You are 18")
else:
    print("You are a child")
    #loops
str = "Python"
for i in str:
    print(i)
        #while loop

