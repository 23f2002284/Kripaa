# Predicted Exam Paper 2025
**Total Marks:** 107 | **Time:** 3 Hours
***

## Section A (Short Answer) - 2 Marks Each
**Q1.** Explain the fundamental principles and purpose of Inter-Process Communication (IPC).    
**Q2.** Explain the basic concepts of file system design and implementation.    
**Q3.** Explain what constitutes a Real-time System. Illustrate with an example.    
**Q4.** Outline the primary techniques for managing free space in a storage system.    
**Q5.** Identify the three distinct categories of operating system schedulers and elaborate on the primary responsibility associated with each.
**Q6.** What are distributed file systems? Provide an example and its use case.

## Section B (Medium Answer) - 5 Marks Each
**Q1.** What constitutes a safe state in a resource allocation system? Elaborate on its role concerning the occurrence of deadlocks.
**Q2.** Detail the concepts of Distributed Systems in an OS.
**Q3.** Discuss the fundamental role of an operating system in managing Input/Output operations.
**Q4.** Contrast internal and external fragmentation.
**Q5.** Discuss the architectural support for atomic operations essential for concurrent process synchronization.
**Q6.** A system administrator observes that a server's performance is significantly degraded, exhibiting high disk I/O activity despite consistently low CPU utilization. The operating system on this server utilizes a paging-based virtual memory system with a fixed amount of swap space. Explain how excessive swapping could lead to this observed behavior. Furthermore, describe one common operational adjustment a system administrator could make to mitigate this issue.
**Q7.** A user initiates the execution of a new application program (e.g., by double-clicking an icon). Identify and briefly describe how at least three distinct operating system services are utilized by the OS to facilitate this program launch, from the moment of initiation until the program begins its execution.
**Q8.** Explain the abstract view of an Operating System with a neat diagram.
**Q9.** Consider a multi-threaded system where a maximum of 4 concurrent threads can access a shared, limited resource (e.g., a pool of database connections). Multiple threads `T1, T2, ..., Tn` repeatedly attempt to acquire and then release an instance of this resource.

Using semaphores, design a mechanism to ensure that:
a) No more than 4 threads can concurrently access the shared resource.
b) Any thread attempting to acquire the resource when all 4 instances are in use will block until an instance becomes available.

Clearly define the semaphore(s) needed, their initial values, and illustrate the semaphore operations (wait/signal or P/V) within the pseudocode for a generic thread `Ti`.

## Section C (Long Answer) - 10 Marks Each
**Q1.** Consider the following page reference string
1,2,3,4,5,3,4,1,6,7,8,7,8,1,7,6,2,5,4,5,3,2
Calculate the number of page faults in each case using the following
algorithms:

(i) FIFO
(ii) LRU
(iii) Optimal
Assume the memory size is 4 frames.
**Q2.** Define the concept of a thread in the context of concurrent programming. Subsequently, compare and contrast user-level threads and kernel-level threads, elaborating on the key advantages and disadvantages associated with each threading model.
**Q3.** Elaborate on the distinct multi-threading paradigms that an operating system can support. Critically assess the design choices and performance implications of each, concluding which model offers superior overall efficiency and flexibility.
**Q4.** Detail the hierarchical organization of data within a hard disk drive, distinguishing between its physical and logical components.
**Q5.** Explain in detail about Banker’s algorithm with example in deadlock. Consider a system that contains four processes P1, P2, P3, P4 and the three resource types R1, R2 and R3. Following are the resource types: R1 has 12, R2 has 8 and the resource type R3 has 10 instances.

|Process|Allocation (R1 R2 R3)|Max (R1 R2 R3)|
|---|---|---|
|P1|0 1 0|7 5 3|
|P2|2 0 0|3 2 2|
|P3|3 0 2|9 0 2|
|P4|2 1 1|2 2 2|

Available (R1 R2 R3): 5 6 7

Answer the following questions using the banker's algorithm:
a) What is the reference of the need matrix?
b) Determine if the system is safe or not.
c) What will happen if the resource request (1, 0, 0) for process P3 can the system accept this request immediately?