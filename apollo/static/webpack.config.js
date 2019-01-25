const path = require('path');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const ManifestRevisionPlugin = require('manifest-revision-webpack-plugin');
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');

module.exports = {
    entry: {
        main: './src/main.js'
    },
    output: {
        path: path.resolve(__dirname, 'dist'),
        publicPath: 'dist/',
        chunkFilename: '[name].[chunkhash].js',
        filename: '[name].[chunkhash].js'
    },
    mode: 'production',
    module: {
        rules: [
            {
                test: /\.(sc|sa|c)ss$/,
                use: [
                    'style-loader',
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
        new ManifestRevisionPlugin(path.join('dist', 'manifest.json'),
            {
                rootAssetPath: './dist'
            }
        )
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
            })
        ]
    }
}
