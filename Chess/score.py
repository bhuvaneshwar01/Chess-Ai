import math

def Probability(rating1,rating2):
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10,1.0*(rating1-rating2)))

def EloRating(Ra,Rb,K,d):
    Pb = Probability(Ra,Rb)
    Pa = Probability(Rb,Ra)

    if d == 1:
        Ra = Ra + K * (1-Pa)
        Rb = Rb + K * (0-Pb)
    else:
        Ra = Ra + K * (0 - Pa)
        Rb = Rb + K * (1 - Pb)

    print("Updated Ratings:-")
    print("Ra =", round(Ra, 6), " Rb =", round(Rb, 6))

Ra = int(input("Enter Rating A : "))
Rb = int(input("Enter Rating b : "))
K = 20
win = input("Win 'w/b' : ")
d = 1 if win == 'w' else 0
EloRating(Ra,Rb,K,d)