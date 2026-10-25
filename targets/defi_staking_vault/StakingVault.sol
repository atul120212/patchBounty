// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Real vulnerable microservice: DeFi Staking Vault.
/// Contains 2 genuine bugs: Reentrancy (CWE-841) and tx.origin auth (CWE-477).
contract StakingVault {
    address public owner;
    mapping(address => uint256) public balances;

    constructor() {
        owner = msg.sender;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdrawAll() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "nothing to withdraw");
        // BUG 1 (CWE-841 CRITICAL): External call BEFORE balance update = reentrancy drain
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");
        balances[msg.sender] = 0;
    }

    function sweepTreasury(address payable to) external {
        // BUG 2 (CWE-477 HIGH): tx.origin auth can be phished via an intermediary contract
        require(tx.origin == owner, "not owner");
        to.transfer(address(this).balance);
    }
}
