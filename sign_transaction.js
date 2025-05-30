const fs = require('fs').promises;
const { CardanoWasm } = require('@emurgo/cardano-serialization-lib-nodejs');

async function signTransaction(txDataPath) {
    try {
        // Read transaction data
        const txData = JSON.parse(await fs.readFile(txDataPath, 'utf8'));

        // Connect to Yoroi wallet
        if (!window.cardano || !window.cardano.yoroi) {
            throw new Error('Yoroi wallet not detected');
        }
        const yoroi = await window.cardano.yoroi.enable();

        // Build transaction
        const txBuilder = CardanoWasm.TransactionBuilder.new();
        txBuilder.add_output(
            CardanoWasm.TransactionOutput.new(
                CardanoWasm.Address.from_bech32(txData.address),
                CardanoWasm.Value.new(CardanoWasm.BigNum.from_str(txData.amount.toString()))
            )
        );

        // Add metadata
        const metadata = CardanoWasm.GeneralTransactionMetadata.new();
        metadata.insert(
            CardanoWasm.BigNum.from_str('674'),
            CardanoWasm.encode_json_str_to_metadatum(JSON.stringify(txData.metadata), 0)
        );
        txBuilder.set_metadata(metadata);

        // Set change address
        txBuilder.set_change_address(CardanoWasm.Address.from_bech32(txData.address));

        // Build unsigned transaction
        const unsignedTx = txBuilder.build();

        // Sign with Yoroi
        const signedTx = await yoroi.signTx(unsignedTx.to_hex());
        const txId = signedTx.tx_hash();

        // Submit transaction
        await yoroi.submitTx(signedTx.to_hex());

        console.log(txId);
    } catch (error) {
        console.error(`Error: ${error.message}`);
        process.exit(1);
    }
}

if (process.argv.length !== 3) {
    console.error('Usage: node sign_transaction.js <tx_data.json>');
    process.exit(1);
}
signTransaction(process.argv[2]);