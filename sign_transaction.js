const fs = require('fs').promises;
const puppeteer = require('puppeteer');
const { CardanoWasm } = require('@emurgo/cardano-serialization-lib-nodejs');

async function signTransaction(txDataPath) {
    let browser;
    try {
        // Read transaction data
        const txData = JSON.parse(await fs.readFile(txDataPath, 'utf8'));

        // Launch browser with Puppeteer
        browser = await puppeteer.launch({
            headless: false,
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });
        const page = await browser.newPage();

        // Inject CardanoWasm and txData into the page
        await page.evaluateOnNewDocument((txData) => {
            window.txData = txData;
        }, txData);

        // Define signing logic in the browser context
        const txId = await page.evaluate(async () => {
            // Check for Yoroi wallet
            if (!window.cardano || !window.cardano.yoroi) {
                throw new Error('Yoroi wallet not detected. Ensure Yoroi extension is installed and enabled.');
            }

            try {
                const yoroi = await window.cardano.yoroi.enable();

                // Load CardanoWasm (injected via exposeFunction)
                const CardanoWasm = window.CardanoWasm;

                // Build transaction
                const txBuilder = CardanoWasm.TransactionBuilder.new();
                txBuilder.add_output(
                    CardanoWasm.TransactionOutput.new(
                        CardanoWasm.Address.from_bech32(window.txData.address),
                        CardanoWasm.Value.new(CardanoWasm.BigNum.from_str(window.txData.amount.toString()))
                    )
                );

                // Add metadata
                const metadata = CardanoWasm.GeneralTransactionMetadata.new();
                metadata.insert(
                    CardanoWasm.BigNum.from_str('674'),
                    CardanoWasm.encode_json_str_to_metadatum(JSON.stringify(window.txData.metadata), 0)
                );
                txBuilder.set_metadata(metadata);

                // Set change address
                txBuilder.set_change_address(CardanoWasm.Address.from_bech32(window.txData.address));

                // Build unsigned transaction
                const unsignedTx = txBuilder.build();

                // Sign with Yoroi
                const signedTx = await yoroi.signTx(unsignedTx.to_hex());
                const txId = signedTx.tx_hash();

                // Submit transaction
                await yoroi.submitTx(signedTx.to_hex());

                return txId;
            } catch (error) {
                throw new Error(`Yoroi signing error: ${error.message}`);
            }
        });

        await browser.close();
        console.log(txId);
        return txId;
    } catch (error) {
        console.error(`Error: ${error.message}`);
        if (browser) await browser.close();
        process.exit(1);
    }
}

if (process.argv.length !== 3) {
    console.error('Usage: node sign_transaction.js <tx_data.json>');
    process.exit(1);
}
signTransaction(process.argv[2]);