import random
import string
 
# Returns a random alphanumeric string of length 'length'
def random_key(length):
    return ''.join(random.sample(string.uppercase + string.digits, length))
