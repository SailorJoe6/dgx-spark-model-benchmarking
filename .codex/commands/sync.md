There is a submodule in this repo named mini-swe-agent.  mini-swe-agent is a fork and needs to be synchronized with it's upstream.  We have a lot of branches in our fork of mini-swe-agent which represent all the code changes that live in our fork.  These branches are stacked one on top of another.  We need to synchronize our fork with upstream, then rebase all our stacked branches based on the updated main branch.  However, there are critical dependencies between our branches!  So, you MUST maintain the stacking order.  i.e if BranchA is based on Main, Branch B is stacked on Branch A and Branch C is stacked on Branch B, then it must remain that way after the rebase to preserve the dependency chain.

- Open a beads issue to track this work
- Study the current stacking order.  Document it in your beads issue.  
- Switch to main branch.  
- Use the github CLI to sync 
- Pull with rebase
- walk the stacked branches rebasing each onto it's proper new parent.  
- test at every step of the way! 
- push each branch after tests succeed.  Do this every step of the way.  

