import random
import string
 
# Returns a random alphanumeric string of length 'length'
def random_key(length):
    key = ''
    for i in range(length):
        key += random.choice(string.uppercase + string.digits)
    return key
