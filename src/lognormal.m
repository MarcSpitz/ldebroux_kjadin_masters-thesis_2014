mean = 150;
var = (mean/2)^2;

mu = log( (mean^2) / sqrt(var + mean^2) );
sig = sqrt( log( 1+ (var/(mean^2))))

x = (0:0.1:mean*3);
y = lognpdf(x, mu, sig);

plot(x, y);

z = 1.96;

lb = exp(-z*sig+mu)
ub = exp(z*sig+mu)
