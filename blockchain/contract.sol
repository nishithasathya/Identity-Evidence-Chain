// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract EvidenceRegistry {

    mapping(bytes32 => uint256) private timestamps;

    event EvidenceStored(
        bytes32 indexed evidenceHash,
        uint256 timestamp
    );

    function storeEvidence(bytes32 evidenceHash) public {
        timestamps[evidenceHash] = block.timestamp;

        emit EvidenceStored(
            evidenceHash,
            block.timestamp
        );
    }

    function verifyEvidence(bytes32 evidenceHash)
        public
        view
        returns (bool)
    {
        return timestamps[evidenceHash] != 0;
    }

    function getTimestamp(bytes32 evidenceHash)
        public
        view
        returns (uint256)
    {
        return timestamps[evidenceHash];
    }
}