const merge = require('webpack-merge');
const common = require('./webpack.common.js');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = merge.smart(common, {
    mode: 'development',
    devtool: 'inline-source-map',
    devServer: { contentBase: './dist' },
    plugins: [
        new HtmlWebpackPlugin({
            template: 'src/index.html'
        })
    ]
});
