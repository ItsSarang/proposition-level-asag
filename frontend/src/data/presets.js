export const PRESETS = [
  {
    id: 'primary_key',
    label: 'Relational Databases: Purpose of a Primary Key',
    question:
      'What is the purpose of a primary key in a relational database?',
    referenceAnswer:
      'A primary key uniquely identifies each record in a table.',
    studentAnswer:
      'A primary key uniquely identifies each record in a table and cannot contain NULL values.',
  },
  {
    id: 'polymorphism',
    label: 'Object-Oriented Programming: Polymorphism Mechanisms',
    question:
      'What is polymorphism in object-oriented programming, and what mechanisms facilitate it?',
    referenceAnswer:
      'Polymorphism allows objects of different classes to respond to the same method call with class-specific behaviors through dynamic dispatch.',
    studentAnswer:
      'Polymorphism allows objects of different classes to respond differently to the same method call. It is commonly implemented using method overriding and dynamic dispatch in languages like Java.',
  },
  {
    id: 'stack_heap',
    label: 'Systems Programming: Stack vs Heap Memory Allocation',
    question:
      'What is the difference between stack and heap memory allocation in C++?',
    referenceAnswer:
      'Stack memory is managed automatically by the compiler for local variables, while heap memory is dynamically allocated and freed by the programmer at runtime.',
    studentAnswer:
      'Stack memory is allocated automatically for local function variables, whereas heap memory is allocated dynamically at runtime using pointers and must be manually deallocated.',
  },
  {
    id: 'recursion',
    label: 'Data Structures: Role of a Base Case in Recursion',
    question:
      'What is the role of a base case in a recursive function?',
    referenceAnswer:
      'A base case provides the termination condition that stops recursion and prevents infinite execution.',
    studentAnswer:
      'The base case terminates the recursive calls by returning a direct value without further self-invocation, preventing stack overflow.',
  },
  {
    id: 'variable_scope',
    label: 'Programming Fundamentals: Scope of Local Variables',
    question:
      'What is the scope of a local variable in a function?',
    referenceAnswer:
      'A local variable is accessible only within the function or block in which it is declared.',
    studentAnswer:
      'A local variable has local scope and can only be accessed inside the specific block or function where it is defined.',
  },
];

