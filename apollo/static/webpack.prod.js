const merge = require('webpack-merge');
const common = require('./webpack.common.js');
const path = require('path');
const ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');

module.exports = merge.smart(common, {
    mode: 'production',
    plugins: [
        new ManifestRevisionPlugin(path.join('dist', 'manifest.json'),
            {
                rootAssetPath: './dist'
            }
        )
    ]
});
