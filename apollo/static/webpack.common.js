const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');

module.exports = {
    entry: {
        scripts: './src/scripts.js',
        styles: './src/styles.js',
        'scripts-rtl': './src/scripts-rtl.js',
        'styles-rtl': './src/styles-rtl.js'
    },
    output: {
        path: path.resolve(__dirname, 'dist'),
        chunkFilename: '[id].[chunkhash].js',
        filename: '[name].[chunkhash].js'
    },
    module: {
        rules: [
            {
                test: /\.(sc|sa|c)ss$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    'css-loader',
                    {
                        loader: 'postcss-loader',
                        options: {
                            plugins: function () {
                                return [
                                    require('autoprefixer')
                                ];
                            }
                        }
                    },
                    'sass-loader'
                ]
            },
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-env'],
                        plugins: ['@babel/plugin-syntax-dynamic-import']
                    }
                }
            }
        ]
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: '[name].[chunkhash].css',
            chunkFilename: '[id].[chunkhash].css'
        })
    ],
    resolve: {
        extensions: [ '.js' ],
        modules: [
            path.resolve(__dirname, 'src', 'js'),
            'node_modules'
        ],
        alias: {
            jquery: 'jquery/dist/jquery.slim.min.js'
        }
    },
    optimization: {
        minimizer: [
            new UglifyJsPlugin({
                sourceMap: true,
                uglifyOptions: {
                    compress: {
                        drop_console: true,
                        dead_code: true
                    },
                    output: {
                        comments: false
                    }
                }
            }),
            new OptimizeCSSAssetsPlugin()
        ]
    }
}
