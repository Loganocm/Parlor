# 🚀 Parlor Pizza - Comprehensive Deployment Guide

This guide covers deploying the **Parlor** application to AWS.
It provides two paths for the backend: **Elastic Beanstalk** (Recommended) or **EC2 (Docker)**.
The frontend is deployed to **S3 + CloudFront**.

---

## ✅ Prerequisites

1.  **AWS Account** with permissions for EC2, Elastic Beanstalk, S3, and CloudFront.
2.  **AWS CLI** installed and configured locally (`aws configure`).
3.  **Docker Desktop** installed and running.
4.  **Node.js 18+** & **Angular CLI** (`npm install -g @angular/cli`).

---

## 🛠️ Part 1: Backend Deployment (FastAPI)

We will containerize the backend and deploy it to the cloud.

### Step 1: Prepare Docker Image

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Build the Docker image locally to verify:
    ```bash
    docker build -t parlor-backend .
    ```
3.  (Optional) Tag and push to **Amazon ECR** if using specialized ECS setups, but for Beanstalk/EC2, we can just use the source bundle or Docker Hub.

---

### Option A: Elastic Beanstalk (Recommended)

_Best for: Easy management, auto-scaling, built-in health checks._

1.  **Initialize Beanstalk**:
    ```bash
    pip install awsebcli
    eb init -p docker parlor-backend-prod
    ```
2.  **Create Environment**:
    ```bash
    eb create parlor-prod-env --instance_type t3.micro
    ```
3.  **Set Environment Variables**:
    Go to the AWS Console -> Elastic Beanstalk -> parlor-prod-env -> Configuration -> Software -> **Environment Properties** and add:
    - `GOOGLE_PLACES_API_KEY`: [Your Key]
    - `GEMINI_API_KEY`: [Your Key]
    - `PORT`: 8000
4.  **Deploy**:
    ```bash
    eb deploy
    ```
    _The API will be available at `http://parlor-prod-env.xxxx.region.elasticbeanstalk.com`._

---

### Option B: EC2 (Manual Docker)

_Best for: Full control, lower cost for single instance._

1.  **Launch EC2 Instance**:
    - OS: Amazon Linux 2023 or Ubuntu.
    - Security Group: Allow Inbound Ports **22 (SSH)**, **80 (HTTP)**, and **8000 (API)**.
2.  **Install Docker on EC2**:
    ```bash
    ssh -i your-key.pem ec2-user@your-ip
    sudo yum update -y
    sudo yum install docker -y
    sudo service docker start
    sudo usermod -a -G docker ec2-user
    # Log out and back in
    ```
3.  **Deploy Code**:
    - Copy `backend/` folder to EC2 (via SCP or Git Clone).
4.  **Run Container**:

    ```bash
    # Create .env file with your secrets
    echo "GOOGLE_PLACES_API_KEY=your_key" > .env
    echo "GEMINI_API_KEY=your_key" >> .env

    # Build and Run
    docker build -t parlor-backend .
    docker run -d \
      -p 80:8000 \
      --env-file .env \
      --restart unless-stopped \
      parlor-backend
    ```

    _The API is now live at `http://your-ec2-ip`._

---

## 🎨 Part 2: Frontend Deployment (Angular)

We simply build the static files and host them.

### Step 1: Update Environment

Open `src/environments/environment.prod.ts` and set the `apiUrl` to your live backend URL (from Part 1).

```typescript
export const environment = {
  production: true,
  apiUrl: "http://parlor-prod-env.xxxx.elasticbeanstalk.com/api", // No trailing slash
};
```

### Step 2: Production Build

Run the build command from the root directory:

```bash
ng build --configuration production
```

_Output will be in `dist/demo/browser` (or similar depending on angular.json)._

### Step 3: Deploy to S3 + CloudFront

1.  **Create S3 Bucket**: name it `parlor-frontend-prod`.
2.  **Upload Files**:
    ```bash
    aws s3 sync dist/demo/browser s3://parlor-frontend-prod --acl public-read
    ```
3.  **Enable Static Hosting**:
    - Go to S3 -> Properties -> Static Website Hosting -> Enable.
    - Index Document: `index.html`.
    - Error Document: `index.html` (Important for Angular routing).
4.  **(Optional but Recommended) CloudFront**:
    - Create a CloudFront distribution pointing to the S3 bucket domain.
    - This provides HTTPS setup automatically.

---

## 🔄 Updating Deployment

**Backend**:

1.  Commit changes.
2.  Run `eb deploy` (Beanstalk) or `git pull && docker build...` (EC2).

**Frontend**:

1.  Run `ng build --configuration production`.
2.  Run `aws s3 sync ...`.
