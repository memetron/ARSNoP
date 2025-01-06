# **ARSNoP (A Roughly Sufficient Number of Parsers)**

ARSNoP is a collection of parser implementations for various types of grammars, offering tools for building and utilizing parsers. 
It includes a range of algorithms designed for different parsing needs, from deterministic context-free grammars to ambiguous grammars.

---

## **Included Parsers**

### **1. LR Parsers**
LR parsers are a class of bottom-up parsers that use action and goto tables to guide parsing. They are efficient for deterministic context-free grammars, operating in linear time under certain conditions. This collection includes the following:

#### **LR(0)**
- Parses grammars without any lookahead.
- Suitable for simple, unambiguous grammars.
- Limited in practical applications due to its inability to resolve many common conflicts.

#### **SLR(1) (Simple LR)**
- Extends LR(0) by using the follow set as a single token of lookahead, enabling it to handle a broader range of grammars.
- More practical than LR(0) but still limited for complex grammars.

#### **LR(1) (Canonical LR)**
- Uses one symbol of lookahead for precise decision-making.
- Handles a wider range of grammars than SLR(1).
- Generates larger parsing tables, which can increase memory usage.

#### **LALR(1) (Look-Ahead LR)**
- Combines canonical LR(1) states with identical kernels to reduce table size.
- Offers a compromise between the power of LR(1) and the smaller tables of SLR(1).
- Commonly used in tools like YACC and Bison.

### **2. Earley Parser**
The Earley parser is a top-down algorithm capable of handling any context-free grammar, including ambiguous ones. It constructs parsing tables dynamically during execution.

#### **Features:**
- Handles ambiguous grammars and generates parse forests for all interpretations.
- Time complexity:
  - **O(n³)** in the general case.
  - **O(n²)** for unambiguous grammars.
  - **O(n)** for grammars that are subsets of LR(k).
- Does not require pre-computed parsing tables, making it flexible for dynamic input and grammars.
