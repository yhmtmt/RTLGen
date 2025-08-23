# Memo about Compressor Tree Optimization

The implementation of the compressor tree optimization is based on UFO-MAC [1]. I attempted to implement the entire algorithm, but the part successfully integrated here is limited to counting and assigning full and half adders. Other parts, such as interconnect assignment and prefix adder optimization, were not implemented due to perceived issues in their formulation. Before explaining these problems, I should describe a subtle mistake in the ILP formulation for adder assignment that I encountered and corrected.

*   **My modification in adder assignment.**

    Equation (8) in paper [1] describes the constraint of the number of partial products (PPs) in the $i$-th stage's $j$-th column as follows:

    ![equation](https://latex.codecogs.com/svg.latex?pp_{i,j}=pp_{i-1,j}%20-%202f_{i,j}%20-%20h_{i,j}%20+%20f_{i-1,j-1}%20+%20h_{i-1,j-1}%20%5Cquad%20(8))

    Where $f_{i,j}$ and $h_{i,j}$ denote the number of full and half adders in the $i$-th stage's $j$-th column. The last two terms describe the carry bits from the $(i-1)$-th stage's $(j-1)$-th column. The first three terms describe sum output bits from the $(i-1)$-th stage's $j$-th column. Therefore, the equation should correctly be:

    ![equation](https://latex.codecogs.com/svg.latex?pp_{i,j}=pp_{i-1,j}%20-%202f_{i-1,j}%20-%20h_{i-1,j}%20+%20f_{i-1,j-1}%20+%20h_{i-1,j-1})

    My code was implemented with the corrected equation above.

    Moreover, to accelerate convergence, the number of variables in the problem should be minimized. There is an important bound, `stage_max`, which appears in equations (6) and (7):

    ![equation](https://latex.codecogs.com/svg.latex?%5Csum_{i=0}^{stage%5C_max}f_{i,j}=F_j%20%5Cquad%20(6))

    ![equation](https://latex.codecogs.com/svg.latex?%5Csum_{i=0}^{stage%5C_max}h_{i,j}=H_j%20%5Cquad%20(7))

    Where $F_j$ and $H_j$ are constants calculated preliminarily. `stage_max` should be at least greater than or equal to the optimal value. If we can select a value for `stage_max` that is close to the optimal value, the optimization time can also be minimized.

    Paper [1] does not provide the exact value for `stage_max`. In my implementation, I set the value of `stage_max` as follows:

    ![equation](https://latex.codecogs.com/svg.latex?stage%5C_max%20=%20%5Clog_{3/2}%20(%203%5E{%5Clog_2%20(pp%5C_rows/2)}/2%20))

    This represents an upper bound, assuming an infinite number of columns in the partial product array. Considering a middle column in an infinite PP array, where the previous column produces carries identical to the column of interest, we can reduce the PPs in the column by 2/3 per stage using full adders. The solution must be an integer. The bound assumes that `pp_rows` is the nearest larger integer power of 3, and the stages where the number of PPs is reduced to two are rounded up. This might seem like a pessimistic bound, but you can observe that the value is quite close to the optimization results found in `compressor_tree_level_opt.dat`. This data concerns the number of compressor tree stages for Normal and Booth4 multipliers. The optimal values and maximum values expected by the equation above are close.

    ![Compressor Tree Stages: Optimal vs. Predicted Max](compressor_tree_stages.png)

    I doubt if there is a more straightforward assignment algorithm.

*   **Is the interconnection assignment formulation really ILP?**

    The author formulated interconnect assignment as optimizing permutation matrices. In each stage, arbitrary wire swapping is feasible in terms of functionality. This is formulated as a 2-D matrix with only one '1' in each column and row. Equation (21) expresses this constraint. However, equation (20) further restricts this, allowing only diagonal elements to be '1'. Therefore, the only possible solution is an identity matrix. Even if we remove this constraint, the approach might not be an ILP formulation because the final optimization target is maximum delay. We would need to multiply the permutation matrix by the input delay vector to compute the output delay vector in each stage. Delay vectors accumulate through the stages, and the optimization target is the maximum value of the final output delay vector, as described in equations (22) and (23). However, the authors did not show any equation accumulating delays through compressor trees. This operation obviously includes multiplications of delay vectors and permutation matrices, both of which are variables. This cannot be fed into an ILP solver. That is why I did not implement the interconnection swapping.

*   **What does the prefix graph optimization do?**

    The `GraphOpt` procedure in Algorithm 2 simply does not work for both depth and fanout optimizations. Additionally, the fanout optimization example in Figure 9 shows an increase in the fanout of input nodes, which I cannot understand the meaning of. Prefix graph optimization is a well-studied topic and is not a trivial problem. Thus, I did not implement the prefix graph optimization algorithm presented in the paper. (My current implementation is merely a ripple carry adder.) I am planning to implement different ones from older works.

## References

[1] UFO-MAC: A Unified Framework for Optimization of High-Performance Multipliers and Multiply-Accumulators.
