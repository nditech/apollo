const path = require('path');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');

var config = {
    entry: {
        scripts: './src/scripts.js',
        styles: './src/styles.js'
    },
    output: {
        path: path.resolve(__dirname, 'dist'),
        chunkFilename: '[id].[chunkhash].js',
        filename: '[name].[chunkhash].js'
    },
    mode: 'production',
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
        new CleanWebpackPlugin(['dist']),
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

module.exports = (env, argv) => {
    if (argv.mode === 'development') {
        config.devtool = 'inline-source-map';
        config.devServer = { contentBase: './dist' };
        config.plugins.push(
            new HtmlWebpackPlugin({
                template: 'src/index.html'
            }));
    } else if (argv.mode === 'production') {
        config.plugins.push(
            new ManifestRevisionPlugin(path.join('dist', 'manifest.json'),
                {
                    rootAssetPath: './dist'
                }
            ));
    }

    return config;
};
