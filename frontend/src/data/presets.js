/**
 * Demonstration presets for ASAG Lab Workbench.
 * Note: Clearly labelled as demonstration examples, not research datasets.
 */

export const PRESETS = [
  {
    id: "polymorphism",
    corpusName: "Polymorphism mechanisms in Object-Oriented Programming",
    domain: "Computer Science // Object-Oriented Design",
    title: "Polymorphism Mechanisms (OOP)",
    tag: "Core + Validated Synthesis",
    question: "What is polymorphism in object-oriented programming, and what mechanisms facilitate it?",
    referenceAnswer: "Polymorphism allows objects of different classes to be treated through a common interface, responding to the same method invocation with class-specific behaviors.",
    studentAnswer: "Polymorphism allows objects of different classes to respond differently to the same method call. It is commonly implemented using method overriding and dynamic dispatch in languages like Java.",
  },
  {
    id: "pk_correct_extra",
    corpusName: "Relational Database Integrity & Primary Keys",
    domain: "Computer Science // Database Systems",
    title: "Primary Key: Correct Additional Info",
    tag: "Correct Extra (+Bonus)",
    question: "What is the purpose of a primary key?",
    referenceAnswer: "A primary key uniquely identifies each record in a table.",
    studentAnswer: "A primary key uniquely identifies each record in a table and cannot contain NULL values.",
  },
  {
    id: "pk_incorrect_extra",
    corpusName: "Relational Database Integrity & Primary Keys",
    domain: "Computer Science // Database Systems",
    title: "Primary Key: Incorrect Contradiction",
    tag: "Misconception (-Penalty)",
    question: "What is the purpose of a primary key?",
    referenceAnswer: "A primary key uniquely identifies each record in a table.",
    studentAnswer: "A primary key uniquely identifies each record in a table and can contain duplicate values.",
  },
  {
    id: "pk_irrelevant_extra",
    corpusName: "Relational Database Integrity & Primary Keys",
    domain: "Computer Science // Database Systems",
    title: "Primary Key: Irrelevant Additional Info",
    tag: "Irrelevant (Zero Effect)",
    question: "What is the purpose of a primary key?",
    referenceAnswer: "A primary key uniquely identifies each record in a table.",
    studentAnswer: "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s.",
  },
  {
    id: "bst",
    corpusName: "Binary Search Tree Invariant & Structure",
    domain: "Computer Science // Data Structures",
    title: "Binary Search Tree Ordering",
    tag: "Domain Synthesis",
    question: "What is a binary search tree?",
    referenceAnswer: "A binary search tree is a binary tree where the left child of a node has a key less than the parent and the right child has a key greater than the parent.",
    studentAnswer: "A binary tree where nodes to the left are smaller and nodes to the right are greater than the root. An AVL tree is a balanced binary search tree.",
  },
  {
    id: "compiler",
    corpusName: "Compiler Translation & Machine Code",
    domain: "Computer Science // Systems",
    title: "Compiler Function Paraphrase",
    tag: "Exact Entailment",
    question: "What is a compiler?",
    referenceAnswer: "A compiler converts high-level source code into machine code.",
    studentAnswer: "A compiler translates high-level programming language code into executable machine code.",
  },
];
