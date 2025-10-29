
def gmsk_pre(bits_32, reset=False):
  

    if reset:
        prev = 0
        alter = 0
    else:

        # ensuring each word starting with initial assignings
        
        prev = 0
        alter = 0

    out_bits = []             # list to store the output bits

    for bit in bits_32:
        b = bit ^ prev        # xor with prev_bit
        a = b ^ alter         # output by xor 
        out_bits.append(a)
        prev = bit
        alter ^= 1            # toggle 

    return out_bits
