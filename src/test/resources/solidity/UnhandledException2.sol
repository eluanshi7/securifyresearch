pragma solidity 0.4.24;

contract C{
    function f() public {
        if(sha256(msg.data) < 2){
            bool b = msg.sender.send(3);
            if(!b) {
                // throw;
            }
        }
    }
}
