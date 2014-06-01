 % @author: Debroux Léonard  <leonard.debroux@gmail.com>
 % @author: Kevin Jadin      <contact@kjadin.com>

mean = 150;
var = (mean/2)^2;


% conversion from normal distribution to log-normal
mu = log( (mean^2) / sqrt(var + mean^2) );
sig = sqrt( log( 1+ (var/(mean^2))))


% plot the log-normal distribution
x = (0:0.1:mean*3);
y = lognpdf(x, mu, sig);

plot(x, y);


% interval of confidence of 95%
z = 1.96;

lb = exp(-z*sig+mu)
ub = exp(z*sig+mu)
