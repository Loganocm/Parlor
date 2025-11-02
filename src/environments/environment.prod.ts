// Production environment configuration
// Update this with your actual backend URL (ALB DNS name or custom domain)
export const environment = {
  production: true,
  // Change this to your deployed backend URL on port 80
  // Example: 'http://your-alb-dns-name.us-east-1.elb.amazonaws.com/api'
  // or 'http://api.yourdomain.com/api' if using a custom domain
  apiUrl: 'http://ec2-3-145-152-149.us-east-2.compute.amazonaws.com/api'
};
