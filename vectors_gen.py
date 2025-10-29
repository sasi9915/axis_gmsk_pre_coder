import csv
import os
import random
from pre_coder import gmsk_pre  

# -------------------------------
# Helper functions
# -------------------------------
def words_to_bits(words):
    bits = []
    for w in words:
        for i in range(32):
            bits.append((w >> i) & 1)
    return bits

def bits_to_words(bits):
    words = []
    for i in range(0, len(bits), 32):
        chunk = bits[i : i + 32]
        val = 0
        for j, b in enumerate(chunk):
            val |= (b << j)
        words.append(val)
    return words

def bin_to_int(bin_str):
    if bin_str.startswith("0b"):
        return int(bin_str, 2)
    else:
        raise ValueError("Input should start with 0b")

# -------------------------------
# Main function to generate CSV
# -------------------------------
def generate_vectors(n=10, out_csv="vectors_gen.csv"):
   
   
    in_words = [random.getrandbits(32) for _ in range(n)]
    out_words = []

    for w in in_words:
        bits = words_to_bits([w])

        # reset precoder for each word

        out_bits = gmsk_pre(bits, reset=True)  
        ow = bits_to_words(out_bits)[0]
        out_words.append(ow)

    # write CSV

    script_dr = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dr, out_csv)

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["input_bin","output_bin"])
        for iw, ow in zip(in_words, out_words):
            writer.writerow([f"0b{iw:032b}", f"0b{ow:032b}"])

    print(f" Generated {n} independent vectors in {file_path}")
    return out_words

# -------------------------------
# Example 
# -------------------------------

if __name__ == "__main__":
    
    generate_vectors(n=20, out_csv="vectors_gen.csv")
